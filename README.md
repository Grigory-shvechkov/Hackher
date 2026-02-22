# Smart Extrude

Smart Extrude is a real-time, vision-assisted monitoring system for extrusion workflows. It combines computer vision, AI-assisted decision logic, and a web-based interface to reduce material waste, energy usage, and operator overhead in makerspaces and fabrication environments.

## Motivation

Built for deployment in the **CICS Makerspace at UMass**, Smart Extrude addresses the need for continuous extrusion monitoring without constant manual supervision, improving both efficiency and sustainability.

## Tech Stack

- **Computer Vision:** YOLO, OpenCV  
- **AI Assistance:** OpenAI  
- **Backend:** Python, Flask (MJPEG video streaming)  
- **Frontend:** SvelteKit  
- **Hardware:** Camera + embedded system (e.g., Raspberry Pi)

## Features

- Live, low-latency video streaming  
- Real-time extrusion monitoring using computer vision  
- Operator-focused web interface  
- Designed for long-running, embedded deployment  

## Getting Started

### Backend
```bash
python server.py

```

### Front end
```bash
npm install
npm run dev
```
