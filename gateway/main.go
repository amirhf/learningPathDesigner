package main

import (
	"log"
	"os"

	"github.com/amirhf/learnpath-gateway/internal/config"
	"github.com/amirhf/learnpath-gateway/internal/handlers"
	"github.com/amirhf/learnpath-gateway/internal/middleware"
	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
	"github.com/joho/godotenv"
)

func main() {
	// Load environment variables
	if err := godotenv.Load(".env.local"); err != nil {
		log.Println("No .env.local file found, using environment variables")
	}

	// Load configuration
	cfg := config.Load()

	// Set Gin mode
	if cfg.Environment == "production" {
		gin.SetMode(gin.ReleaseMode)
	}

	// Create router
	r := gin.Default()

	// CORS configuration
	r.Use(cors.New(cors.Config{
		AllowOrigins:     []string{"http://localhost:3000", "https://*.vercel.app"},
		AllowMethods:     []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
		AllowHeaders:     []string{"Origin", "Content-Type", "Authorization"},
		ExposeHeaders:    []string{"Content-Length"},
		AllowCredentials: true,
	}))

	// Middleware
	r.Use(middleware.RequestID())
	r.Use(middleware.Logger())
	r.Use(middleware.Recovery())

	// Root endpoint - API info
	r.GET("/", func(c *gin.Context) {
		c.JSON(200, gin.H{
			"service": "Learning Path Designer Gateway",
			"version": "1.0.0",
			"status":  "running",
			"message": "Welcome to the Learning Path Designer API Gateway",
			"endpoints": gin.H{
				"info":         "GET /",
				"health":       "GET /health",
				"search":       "POST /api/search",
				"plan":         "POST /api/plan",
				"replan":       "POST /api/plan/:id/replan",
				"quiz_generate": "POST /api/quiz/generate",
				"quiz_submit":   "POST /api/quiz/submit",
			},
			"services": gin.H{
				"rag":     cfg.RAGServiceURL + " (port 8001)",
				"planner": cfg.PlannerServiceURL + " (port 8002)",
				"quiz":    cfg.QuizServiceURL + " (port 8003)",
			},
			"documentation": gin.H{
				"rag":     "http://localhost:8001/docs",
				"planner": "http://localhost:8002/docs",
				"quiz":    "http://localhost:8003/docs",
			},
		})
	})

	// Health check
	r.GET("/health", handlers.HealthCheck(cfg))

	// API routes
	api := r.Group("/api")
	{
		// RAG Service
		api.POST("/search", handlers.Search(cfg))
		
		// Planner Service
		api.POST("/plan", handlers.CreatePlan(cfg))
		api.GET("/plan/:id", handlers.GetPlan(cfg))
		api.GET("/plan/user/:user_id/plans", handlers.GetUserPlans(cfg))
		api.POST("/plan/:id/replan", handlers.Replan(cfg))
		
		// Quiz Service
		api.POST("/quiz/generate", handlers.GenerateQuiz(cfg))
		api.POST("/quiz/submit", handlers.SubmitQuiz(cfg))
	}

	// Start server
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	log.Printf("Starting gateway on port %s", port)
	if err := r.Run(":" + port); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}
}
