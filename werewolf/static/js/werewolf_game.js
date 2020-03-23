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

    skills.select = function () {
        $(this).addClass("selected");
        candidates.push($(this));
        if (candidates.length > num_of_can) {
            candidates.shift().removeClass("selected");
        }
    };

    function reset_panel() {
        tips.text("");
        buttons.html("");
    }

    skills.skill_vote = function () {
        $("#skills").modal("hide");
        tips.text("选择玩家并投票");
        num_of_can = 1;
        buttons.html('<button class="btn btn-warning skill-confirm">投票</button>' + '<button class="btn btn-warning skill-cancel">弃票</button>');
        buttons.children("button.skill-confirm").on("click", function () {
            if (candidates.length !== num_of_can) {
                show_message("所选玩家数量错误，需要选择" + num_of_can + "人");
                return;
            }
            reset_panel();
            $.ajax({
                url: "api/vote?target=" + candidates.shift().attr("pos"),
                dataType: "json",
                success: function (info) {
                    if (info.suc !== true) {
                        show_message(info.msg);
                    }
                }
            });
        });
        buttons.children("button.skill-cancel").on("click", function () {
            reset_panel();
            $.ajax({
                url: "api/vote?target=-1",
                dataType: "json",
                success: function (info) {
                    if (info.suc !== true) {
                        show_message(info.msg);
                    }
                }
            });
        });
    };

    skills.skill_captain = function () {
        $("#skills").modal("hide");
        num_of_can = 0;
        buttons.html('<button class="btn btn-warning skill-elect">竞选</button>' + '<button class="btn btn-warning skill-no-elect">不竞选</button>' + '<button class="btn btn-warning skill-give-up">退水</button>');
        buttons.children("button.skill-elect").on("click", function () {
            reset_panel();
            $.ajax({
                url: "api/elect?choice=yes",
                dataType: "json",
                success: function (info) {
                    if (info.suc !== true) {
                        show_message(info.msg);
                    }
                }
            });
        });
        buttons.children("button.skill-no-elect").on("click", function () {
            reset_panel();
            $.ajax({
                url: "api/elect?choice=no",
                dataType: "json",
                success: function (info) {
                    if (info.suc !== true) {
                        show_message(info.msg);
                    }
                }
            });
        });
        buttons.children("button.skill-give-up").on("click", function () {
            reset_panel();
            $.ajax({
                url: "api/elect?choice=quit",
                dataType: "json",
                success: function (info) {
                    if (info.suc !== true) {
                        show_message(info.msg);
                    }
                }
            });
        });
    };

    skills.skill_wolf_kill = function () {
        $("#skills").modal("hide");
        tips.text("选择玩家落刀");
        num_of_can = 1;
        buttons.html('<button class="btn btn-warning skill-confirm">落刀</button>' + '<button class="btn btn-warning skill-cancel">空刀</button>');
        buttons.children("button.skill-confirm").on("click", function () {
            if (candidates.length !== num_of_can) {
                show_message("所选玩家数量错误，需要选择" + num_of_can + "人");
                return;
            }
            reset_panel();
            $.ajax({
                url: "api/wolf_kill?target=" + candidates.shift().attr("pos"),
                dataType: "json",
                success: function (info) {
                    if (info.suc !== true) {
                        show_message(info.msg);
                    }
                }
            });
        });
        buttons.children("button.skill-cancel").on("click", function () {
            reset_panel();
            $.ajax({
                url: "api/wolf_kill?target=-1",
                dataType: "json",
                success: function (info) {
                    if (info.suc !== true) {
                        show_message(info.msg);
                    }
                }
            });
        });
    };

    skills.skill_discover = function () {
        $("#skills").modal("hide");
        tips.text("选择玩家查验");
        num_of_can = 1;
        buttons.html('<button class="btn btn-warning skill-confirm">查验</button>');
        buttons.children("button.skill-confirm").on("click", function () {
            if (candidates.length !== num_of_can) {
                show_message("所选玩家数量错误，需要选择" + num_of_can + "人");
                return;
            }
            reset_panel();
            $.ajax({
                url: "api/discover?target=" + candidates.shift().attr("pos"),
                dataType: "json",
                success: function (info) {
                    show_message(info.msg);
                }
            });
        });
    };

    window.skills = skills
})(window);

(function (window) {
    let history = $("#history-model-content");

    document.querySelector("#history").onfocus = function () {
        $("#history-model-content").scrollTop($(this).prop("scrollHeight"));
    };

    function update_seats(seats) {
        $("#all_players .player span").each(function () {
            $(this).text("");
        });
        for (const position in seats) {
            let name = seats[position][0];
            $("#all_players button[pos=" + position + "]").siblings("span").text(name);
        }
    }

    gid_source.addEventListener('game_info', function (event) {
        let data = JSON.parse(event.data);
        let show = data.show
        if ("seats" in data) {
            update_seats(data.seats);
        }
        if (data.cards) {
            show_message("身份牌已发放");
            $.ajax({
                url: "api/get_game_info",
                dataType: "json",
                success: function (info) {
                    $(".player > button").on("click", skills.select);
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
                    let skills_html = ""
                    role.skills.forEach(element => {
                        skills_html += '<div><button id="' + element[0].toLowerCase() + '" type="button" class="btn-lg skill-button" onclick="skills.' + element[0].toLowerCase() + '();">' + element[1] + '</button></div>'
                    });
                    $("#skills-model-content").html(skills_html);
                    $("#status-message").text(info.game.status[1])
                }
            });
        }
        if (data.history) {
            let content = '';
            data.history.split('\n').forEach(element => {
                content += '<p>' + element + '</p>'
            });
            if (show) {
                show_message(content);
            }
            history.html(history.html() + content)
        }

        if ("days" in data) {
            $("#status-days").text(data.days)
        }

        if ("game_status" in data) {
            $("#status-message").text(data.game_status)
        }

    }, false);

    // uid_source.addEventListener('game_info', function (event) {
    //     let data = JSON.parse(event.data);
    //     let show = data.show;
    //     if (data.history) {
    //         let content = '';
    //         data.history.split('\n').forEach(element => {
    //             content += '<p>' + element + '</p>';
    //         });
    //         if (show) {
    //             show_message(content);
    //         }
    //         history.html(history.html() + content);
    //     }
    // }, false);

    $.ajax({
        url: "api/get_game_info",
        type: "GET",
        dataType: "json",
        success: function (info) {            
            update_seats(info.game.players);
            let game_status = info.game.status;
            if (game_status[0] === "GAME_STATUS_WAIT_TO_START") {
                $(".player > button").on("click", function () {
                    $.ajax({
                        url: "api/sit?position=" + $(this).attr("pos")
                    });
                }
                );
            } else {
                $(".player > button").off("click");
                $(".player > button").on("click", skills.select);
            }
        }
    });

})(window);

