const mongoose = require("mongoose");

const sensorSchema = new mongoose.Schema({
    device: { type: String, required: true},
    date: { type: Date, default: Date.now },
    windowSize: { type: Number, required: true },
    label: { type: Number, default: null },
    latency: { type: Number, default: null },
    data: { type: Object, required: true },
});

module.exports = mongoose.model("Sensor", sensorSchema);

