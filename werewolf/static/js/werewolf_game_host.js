(function () {
    let bgm_audio = document.querySelector("#bgm_audio");
    let instruction_audio = document.querySelector("#instruction_audio");
    let audio_queue = [];
    let bgm_loop = false;
    let busy = false;
    const before_wait = 1000;
    const after_wait = 1000;

    function move_on() {
        if (busy) {
            return;
        }
        let data = audio_queue.shift();
        if (data === undefined) {
            return;
        }
        busy = true;
        let instruction_src = data[0];
        let bgm_src = data[1];
        bgm_loop = data[2];

        if (bgm_src) {
            bgm_audio.pause();
            bgm_audio.src = bgm_src;
            bgm_audio.play();
        }
        instruction_audio.pause();
        instruction_audio.src = instruction_src;
        setTimeout(function () {
            instruction_audio.play();
        }, before_wait);
    }

    instruction_audio.onended = function () {
        setTimeout(function () {
            if (!bgm_loop) {
                bgm_audio.pause();
            }
            busy = false;
            move_on();
        }, after_wait);
    };

    gid_source.addEventListener('music', function (event) {
        let data = JSON.parse(event.data);
        audio_queue.push(data);
        move_on();
    }, false);

    gid_source.addEventListener('game_info', function (event) {
        let data = JSON.parse(event.data);

        if ("next_step" in data) {
            $("#next-step").text(data.next_step)
        }

    }, false);

    $("#next-step").on("click", function () {
        $.ajax({
            url: "api/next_step",
            dataType: "json",
            success: function (info) {
                if (info.msg !== 'OK') {
                    alert(info.msg)
                }
            }
        });
    });

    $("#deal").on("click", function () {
        bgm_audio.play();
        bgm_audio.pause();
        instruction_audio.play();
        instruction_audio.pause();
        $.ajax({
            url: "api/deal",
            dataType: "json",
            success: function (info) {
                if (info.msg !== 'OK') {
                    alert(info.msg)
                } else {
                    $("#deal").off("click");
                }
            }
        });
    });
})();


