(function (window) {
    let skills = {};
    let tips = $("#ope-panel .tips");
    let buttons = $("#ope-panel .panel-buttons");
    let seats = $("#all_players button");
    let candidates = [];
    let num_of_can = 0;
    let message = $("#message");

    window.show_message = function (content) {
        message.find("#message-model-content").html(content);
        message.modal("show");
    }

    skills.skill_vote = function () {
        $("#skills").modal("hide");
        num_of_can = 1;
        buttons.html('<button class="btn btn-warning skill-confirm">投票</button>' + '<button class="btn btn-warning skill-cancel">弃票</button>');
        seats.on("click", function () {
            $(this).addClass("vote-selected");
            candidates.push($(this));
            if (candidates.length > num_of_can) {
                candidates.shift().removeClass("vote-selected");
            }
        });
        buttons.children("button.skill-confirm").on("click", function () {
            if (candidates.length !== num_of_can) {
                show_message("所选玩家数量错误，需要选择" + num_of_can + "人");
                return;
            }
            $.ajax({
                url: "action?op=vote&target=" + candidates.shift().attr("pos"),
                dataType: "json",
                success: function (info) {
                    if (info.suc !== true) {
                        show_message(info.msg);
                    }
                }
            });
        });
    };


    window.skills = skills
})(window);

(function (window) {
    document.querySelector("#history").onfocus = function () {
        $("#history-model-content").scrollTop($(this).prop("scrollHeight"));
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
            update_seats(data.seats);
        }
        if (data.cards) {
            show_message("身份牌已发放");
            $.ajax({
                url: "get_game_info",
                dataType: "json",
                success: function (info) {
                    $(".player > button").on("click", null);
                    let role = info.role;
                    $("#check-role-dialog .modal-body").html(
                        '<p>' +
                        '你的身份是：' + role.role_type[1] +
                        '</p>' +
                        '<div class="role-img">' +
                        '<img src="static/images/werewolf/cards/' + role.role_type[0].toLowerCase().replace('role_type_', '') + '.jpg"' +
                        'alt="' + role.role_type[1] + '" width="274" height="389">' +
                        '</div>'
                    );
                    let skills = ""
                    role.skills.forEach(element => {
                        skills += '<div><button id="' + element[0].toLowerCase() + '" type="button" class="btn-lg skill-button onclick="skills.' + element[0].toLowerCase() + '();">' + element[1] + '</button></div>'
                    });
                    $("#skills-model-content").html(skills);
                    $("#status-message").text(info.game.status[1])
                }
            });
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
            if (game_status[0] === "GAME_STATUS_WAIT_TO_START") {
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
