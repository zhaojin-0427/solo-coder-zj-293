#!/bin/bash
cd "$(dirname "$0")/frontend"

echo "Installing dependencies..."
npm install

echo "Starting Vue dev server on port 9101..."
npm run dev
