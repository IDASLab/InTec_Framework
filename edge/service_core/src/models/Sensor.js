const mongoose = require("mongoose");
const { v4: uuidv4 } = require("uuid");

const sensorSchema = new mongoose.Schema({
    id: { type: String, default: uuidv4, unique: true },
    device: { type: String, required: true, index: true },
    date: { type: Date, default: Date.now },
    windowSize: { type: Number, required: true },
    label: { type: Number, default: null },
    latency: { type: Number, default: null },
    data: { type: Object, required: true },
});

module.exports = mongoose.model("Sensor", sensorSchema);

