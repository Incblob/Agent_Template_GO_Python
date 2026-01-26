package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
	"time"

	"github.com/go-playground/validator/v10"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
)

const AGENT_URL = "http://127.0.0.1:8000/query_agent"

type contextKey string

const requestIDKey contextKey = "requestID"

func main() {
	router := gin.Default()
	router.SetTrustedProxies(nil)

	router.Use(gin.Recovery())
	router.Use(requestIDMiddleware())
	router.Use(customLoggerMiddleware())

	router.POST("/question", askAgentAPI)

	router.Run("localhost:4000")
}

func requestIDMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		requestID := uuid.New().String()[:5]
		ctx := context.WithValue(c.Request.Context(), requestIDKey, requestID)
		c.Request = c.Request.WithContext(ctx)
		c.Header("X-Request-ID", requestID)
		c.Next()
	}
}

func customLoggerMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		requestID := getID(c.Request.Context())

		start := time.Now()
		c.Next()
		duration := time.Since(start)

		fmt.Printf(
			"[%s] %s %s %d %v\n",
			requestID,
			c.Request.Method,
			c.Request.URL,
			c.Writer.Status(),
			duration,
		)

	}
}

func getID(ctx context.Context) string {
	if id := ctx.Value(requestIDKey); id != nil {
		return id.(string)
	}
	return "missing ID"
}

type Question struct {
	Query string `json:"query" validate:"required,checkReqLength"`
}

func checkReqLength(fl validator.FieldLevel) bool {
	query := fl.Field().String()
	words := strings.Fields(query)
	return len(words) > 2
}

func askAgentAPI(c *gin.Context) {
	var requestbody Question
	if err := c.BindJSON(&requestbody); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error() + "Query under 3 words"})
		return
	}

	validate := validator.New(validator.WithRequiredStructEnabled())
	validate.RegisterValidation("checkReqLength", checkReqLength)

	err := validate.Struct(requestbody)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// make json
	j_req, err := json.Marshal(requestbody)
	if err != nil {
		fmt.Printf("Error marshaling JSON: %v\n", err)
	}

	response, err := http.Post(
		AGENT_URL, "application/json",
		bytes.NewBuffer(j_req),
	)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	defer response.Body.Close()

	c.JSON(http.StatusOK, gin.H{"agent_response": response})
}
