FROM node:16-alpine

WORKDIR /app

COPY package.json package-lock.json ./

RUN npm i

COPY . .

RUN npm run build

ENV PORT=80
EXPOSE ${PORT}

CMD ["npm", "run", "start"]
