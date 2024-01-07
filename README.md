sudo docker build -t colobot .  
sudo docker run -v $(pwd)/bot/db:/app/bot/db --network="host" -dit colobot
