async function stopRecording(){
        try{
          const startButton = document.getElementById("startBtn");
          startButton.innerHTML = "start";
          await fetch('http://127.0.0.1:5000/stop-recording');
        }
        catch(error){
          console.error('Error stopping', error);
        }
      }

      async function startRecording(){
        try{
        const startButton = document.getElementById("startBtn");
        startButton.innerHTML = "recording";
        const response = await fetch('http://127.0.0.1:5000/start-recording');
        const data = await response.json();
        console.log("timeline data !", data);
        getVideo(data);
      }
      catch (error) {
        console.error('Error game stats', error)
      }
      }


    async function getVideo(timelineData){
        try{
          const video = document.getElementById("vod");
          const seekbar = document.getElementById("seekbar");
          
          const response = await fetch('http://127.0.0.1:5000/get-video');
          const data = await response.json();
          const videoPath = `file:///${data.replace(/\\/g, '/')}`;
          console.log(videoPath);

          document.getElementById("vod-source").src = videoPath;
          document.getElementById("vod").load();

          video.addEventListener("loadedmetadata", () => {
            seekbar.max = video.duration;
            document.getElementById("vod-placeholder").style.display = "none";

          });
          
          video.addEventListener("timeupdate", () => {
            if (video.duration) {
              // seekbar.value = (video.currentTime / video.duration) * 100;
              seekbar.value = video.currentTime;
              }
          });
          seekbar.addEventListener("input", () => {
            video.currentTime = seekbar.value;
          })

          const events = timelineData.map(event => event.vod_time);
          console.log(events);
          for (let i = 0; i < Object.keys(timelineData).length; i++){
            events.push(Object.keys(timelineData)[i]);
          }
          const datalist = document.getElementById("tickmarks");
          datalist.innerHTML = "";

          events.forEach(time => {
            const option = document.createElement("option");
            option.value = Math.round(time); 
            print(option.value)
            datalist.appendChild(option);
          });


        }
        catch (error){
          console.error('Error fetching data: ', error)
        }
    }

    async function play(){
      if (vod.paused){
        vod.play()
      }
      else{
        vod.pause();
      }
    }

    async function getTicks(){
      try{
        const response = await fetch('http://127.0.0.1:5000/game-stats');
        const data = response.json();
        console.log(data);
      }
      catch{
        console.error('Error game stats', error)
      }
    }