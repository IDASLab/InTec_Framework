require("dotenv").config();
const express = require("express");
const connectDB = require("./src/config/database");
const app = require("./src/app");
const logger = require("./src/utils/logger");

const PORT = process.env.PORT || 1010;

// Connect to Database
connectDB();

// Start Server
app.listen(PORT, "0.0.0.0", () => {
    logger.info(`🚀 Server is running on http://0.0.0.0:${PORT}`);
});

// Handle Uncaught Errors
process.on("uncaughtException", (err) => {
    logger.error(`❌ Uncaught Exception: ${err.message}`);
    process.exit(1);
});

process.on("unhandledRejection", (reason, promise) => {
    logger.error(`⚠️ Unhandled Promise Rejection at: ${promise}, reason: ${reason}`);
});

