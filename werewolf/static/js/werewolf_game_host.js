(function () {
    let back_audio = document.querySelector("#back_audio");
    let step_audio = document.querySelector("#step_audio");
    let audio_queue = [];

    function play() {
        console.log("play")
        let data = audio_queue.shift();
        if (data === undefined) {
            return;
        }
        let step_src = data[0];
        let back_src = data[1];
        if (back_src !== 'same') {
            back_audio.pause();
        }
        back_audio.src = back_src;
        back_audio.play();
        step_audio.src = step_src;
        step_audio.play();
    }

    step_audio.onended = function () {
        play()
    };

    gid_source.addEventListener('music', function (event) {
        let data = JSON.parse(event.data);
        audio_queue.push(data);
        if (step_audio.paused) {
            play();
        }
    }, false);

    gid_source.addEventListener('music_stop', function (event) {
        audio_queue = [];
        back_audio.pause();
        step_audio.pause();
    }, false);

    $("#next-step").on("click", function () {
        $.ajax({
            url: "action?op=next_step"
        });
    });

    $("#deal").on("click", function () {
        $.ajax({
            url: "action?op=deal"
        });
    });

})();


