(function (window) {
    document.querySelector("#history").onfocus = function () {
        $("#history-model-content").scrollTop(this.prop("scrollHeight"));
    };

    function update_seats(seats) {
        $("#all_players .player span").each(function () {
            $(this).text("");
        });
        for (const position in seats) {
            let name = seats[position];
            $("#all_players button[pos=" + position + "]").siblings("span").text(name);
        }
    }

    common_source.addEventListener('game_info', function (event) {
        let data = JSON.parse(event.data);
        if ("seats" in data) {
            console.log(data.seats);

            update_seats(data.seats);
        }
    }, false);

    $.ajax({
        url: "get_game_info",
        type: "GET",
        dataType: "json",
        success: function (info) {
            let seats = {}
            info.game.roles.forEach(role => {
                seats[role[1]] = role[2];
            });
            update_seats(seats);
            let game_status = info.game.status;
            if (game_status === "GAME_STATUS_WAIT_TO_START") {
                $(".player > button").on("click", function () {
                    $.ajax({
                        url: "action?op=sit&position=" + $(this).attr("pos")
                    });
                }
                );
            }

        }
    });

})(window);













/*
 * @Author: Lucien Zhang
 * @Date:   2019-09-29 18:02:32
 * @Last Modified by:   Lucien Zhang
 * @Last Modified time: 2019-10-09 14:30:35
 */

// document.querySelector("#history-btn").onclick = function() { $("#history-model-content").scrollTop($("#history-model-content").prop("scrollHeight")); };


// $.ajax({
//         url: "werewolf/game_process",
//         type: "GET",
//         dataType: "json",
//         success: function (data) {
//             let info=$.parseJSON(data);

//         }
//         });
