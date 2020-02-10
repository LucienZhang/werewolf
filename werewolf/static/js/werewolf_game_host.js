(function () {
    let back_audio = document.querySelector("#back_audio");
    let step_audio = document.querySelector("#step_audio");
    let audio_queue = [];
    let stop = false;
    let playing = false;
    let before_wait = 1000;
    let after_wait = 1000;

    function play() {
        playing = true;
        if (stop) {
            back_audio.pause();
            stop = false
        }
        let data = audio_queue.shift();
        if (data === undefined) {
            playing = false;
            return;
        }
        let step_src = data[0];
        let back_src = data[1];
        let repeat = data[2];

        back_audio.loop = repeat;

        if (back_src === 'same') {
            step_audio.src = step_src;
            setTimeout(function () { step_audio.play(); }, before_wait);
        } else if (back_src === 'stop') {
            stop = true
            step_audio.src = step_src;
            setTimeout(function () { step_audio.play(); }, before_wait);
        } else {
            back_audio.src = back_src;
            back_audio.play();
            step_audio.src = step_src;
            setTimeout(function () { step_audio.play(); }, before_wait);
        }
    }

    step_audio.onended = function () {
        setTimeout(play, after_wait);
    };

    gid_source.addEventListener('music', function (event) {
        let data = JSON.parse(event.data);
        audio_queue.push(data);
        if (step_audio.paused && playing === false) {
            play();
        }
    }, false);

    gid_source.addEventListener('music_stop', function (event) {
        audio_queue = [];
        back_audio.pause();
        step_audio.pause();
        playing = false
    }, false);

    $("#next-step").on("click", function () {
        $.ajax({
            url: "action?op=next_step",
            dataType: "json",
            success: function (info) {
                if (!info.suc) {
                    alert(info.msg)
                }
            }
        });
    });

    $("#deal").on("click", function () {
        $.ajax({
            url: "action?op=deal",
            dataType: "json",
            success: function (info) {
                if (!info.suc) {
                    alert(info.msg)
                }
            }
        });
    });

})();


