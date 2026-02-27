FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install --only=production

# Copy application source
COPY . .

# Expose React dev server port
EXPOSE 3000
ENV PORT=3000

# Start the React application
CMD ["npm", "start"]
