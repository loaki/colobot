sudo docker build -t colobot .  
sudo docker run --restart unless-stopped -v $(pwd)/bot/db:/app/bot/db --network="host" -dit colobot
