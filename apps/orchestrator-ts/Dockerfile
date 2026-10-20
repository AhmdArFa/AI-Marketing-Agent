FROM node:22-slim
WORKDIR /srv
COPY package.json package-lock.json* ./
RUN npm install
COPY tsconfig.json ./
COPY src ./src
RUN npm run build
CMD ["node", "dist/index.js"]
