# Step 1: Use an official Node.js runtime as a parent image
FROM node:14 as build

# Step 2: Set the working directory in the container
WORKDIR /app

# Step 3: Copy the package.json files from your project into the container
COPY im_server/frontend/package*.json ./

# Step 4: Install any dependencies
RUN npm config set registry https://registry.npmmirror.com && npm install

# Step 5: Copy the rest of your app's source code from your project into the container
COPY im_server/frontend .

# Step 6: Your app binds to port 3000 so you'll use the EXPOSE instruction to have it mapped by the docker daemon
# EXPOSE 3000

# Step 7: Define the command to run your app using CMD which defines your runtime
# CMD ["npm", "run", "build"]
RUN npm run build

# Stage 2: Serve the application with Nginx
FROM nginx:alpine

COPY --from=build /app/build /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
