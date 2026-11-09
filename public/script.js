    async function stopRecording(){
        try{
          const startButton = document.getElementById("startBtn");
          startButton.innerHTML = "start";
          await fetch('http://127.0.0.1:5000/start-recording?recording=false');
        }
        catch(error){
          console.error('Error stopping', error);
        }
      }

    async function startRecording(){
        try{
        const startButton = document.getElementById("startBtn");
        startButton.innerHTML = "recording";
        const response = await fetch('http://127.0.0.1:5000/start-recording?recording=true');
        const data = await response.json();
        console.log("timeline data !", data);
        // only a finished recording returns a list of events; errors and
        // "Already recording" come back as an object
        if (Array.isArray(data)) {
          getVideo(data);
        }
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
          const datalist = document.getElementById("tickmarks");
          datalist.innerHTML = "";

          console.log("response", response);

          events.forEach(time => {
            const option = document.createElement("option");
            option.value = Math.round(time); 
            console.log(option.value)
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
        const data = await response.json();
        console.log(data);
      }
      catch (error){
        console.error('Error game stats', error)
      }
    }