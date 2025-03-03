const express = require("express");
const cors = require("cors");
const morgan = require("morgan");
const sensorRoutes = require("./routes/sensorRoutes");
const logger = require("./utils/logger");

const app = express();

// Middleware for logging requests
app.use(morgan("combined", { stream: { write: (message) => logger.info(message.trim()) } }));

// Enable CORS
app.use(cors());

// API Routes
app.use("/", sensorRoutes);

// Global Error Handler (Catches unhandled errors)
app.use((err, req, res, next) => {
    logger.error(`❌ Error: ${err.message}`);
    res.status(500).json({ status: "error", message: "Internal Server Error" });
});

module.exports = app;

