(function (window) {
    let skills = {};
    let tips = $("#ope-panel .tips");
    let buttons = $("#ope-panel .panel-buttons");
    let seats = $("#all_players button");
    let candidates = [];
    let num_of_can = 0;
    let message = $("#message");
    let history = $("#history-model-content");

    window.add_history = function (data, show) {
        if (!data) {
            return
        }
        let content = '';
        data.split('\n').forEach(element => {
            content += '<p>' + element + '</p>'
        });
        if (show) {
            show_message(content);
        }
        history.html(history.html() + content)
    }

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

    skills.deselect = function () {
        while (candidates.length > 0) {
            candidates.shift().removeClass("selected");
        }
    };

    function reset_panel() {
        tips.text("");
        buttons.html("");
        skills.deselect();
        $('#all_players').removeClass();

    }

    skills.skill_vote = function () {
        $('#all_players').addClass('skill_vote');
        $("#skills").modal("hide");
        tips.text("选择玩家并投票");
        num_of_can = 1;
        buttons.html('<button class="btn btn-warning skill-confirm">投票</button>' + '<button class="btn btn-warning skill-cancel">弃票</button>');
        buttons.children("button.skill-confirm").on("click", function () {
            if (candidates.length !== num_of_can) {
                show_message("所选玩家数量错误，需要选择" + num_of_can + "人");
                return;
            }
            $.ajax({
                url: "api/vote?target=" + candidates[0].attr("pos"),
                dataType: "json",
                success: function (info) {
                    if (info.msg !== 'OK') {
                        show_message(info.msg);
                    } else {
                        add_history(info.result, true);
                    }
                }
            });
            reset_panel();
        });
        buttons.children("button.skill-cancel").on("click", function () {
            $.ajax({
                url: "api/vote?target=-1",
                dataType: "json",
                success: function (info) {
                    if (info.msg !== 'OK') {
                        show_message(info.msg);
                    } else {
                        add_history(info.result, true);
                    }
                }
            });
            reset_panel();
        });
    };

    skills.skill_captain = function () {
        $('#all_players').addClass('skill_captain');
        $("#skills").modal("hide");
        num_of_can = 1;
        buttons.html('<button class="btn btn-warning skill-elect">竞选</button>' + '<button class="btn btn-warning skill-give-up">退水</button>' + '<button class="btn btn-warning skill-handover">移交警徽</button>');
        buttons.children("button.skill-elect").on("click", function () {
            $.ajax({
                url: "api/elect?choice=yes",
                dataType: "json",
                success: function (info) {
                    if (info.msg !== 'OK') {
                        show_message(info.msg);
                    } else {
                        add_history(info.result, true);
                    }
                }
            });
            reset_panel();
        });
        buttons.children("button.skill-give-up").on("click", function () {
            $.ajax({
                url: "api/elect?choice=quit",
                dataType: "json",
                success: function (info) {
                    if (info.msg !== 'OK') {
                        show_message(info.msg);
                    } else {
                        add_history(info.result, true);
                    }
                }
            });
            reset_panel();
        });
        buttons.children("button.skill-handover").on("click", function () {
            $.ajax({
                url: "api/handover?target=" + candidates[0].attr("pos"),
                dataType: "json",
                success: function (info) {
                    if (info.msg !== 'OK') {
                        show_message(info.msg);
                    } else {
                        add_history(info.result, true);
                    }
                }
            });
            reset_panel();
        });
    };

    skills.skill_wolf_kill = function () {
        $('#all_players').addClass('skill_wolf_kill');
        $("#skills").modal("hide");
        tips.text("选择玩家落刀");
        num_of_can = 1;
        buttons.html('<button class="btn btn-warning skill-confirm">落刀</button>' + '<button class="btn btn-warning skill-cancel">空刀</button>');
        buttons.children("button.skill-confirm").on("click", function () {
            if (candidates.length !== num_of_can) {
                show_message("所选玩家数量错误，需要选择" + num_of_can + "人");
                return;
            }
            $.ajax({
                url: "api/wolf_kill?target=" + candidates[0].attr("pos"),
                dataType: "json",
                success: function (info) {
                    if (info.msg !== 'OK') {
                        show_message(info.msg);
                    } else {
                        add_history(info.result, true);
                    }
                }
            });
            reset_panel();
        });
        buttons.children("button.skill-cancel").on("click", function () {
            $.ajax({
                url: "api/wolf_kill?target=-1",
                dataType: "json",
                success: function (info) {
                    if (info.msg !== 'OK') {
                        show_message(info.msg);
                    } else {
                        add_history(info.result, true);
                    }
                }
            });
            reset_panel();
        });
    };

    skills.skill_discover = function () {
        $('#all_players').addClass('skill_discover');
        $("#skills").modal("hide");
        tips.text("选择玩家查验");
        num_of_can = 1;
        buttons.html('<button class="btn btn-warning skill-confirm">查验</button>');
        buttons.children("button.skill-confirm").on("click", function () {
            if (candidates.length !== num_of_can) {
                show_message("所选玩家数量错误，需要选择" + num_of_can + "人");
                return;
            }
            $.ajax({
                url: "api/discover?target=" + candidates[0].attr("pos"),
                dataType: "json",
                success: function (info) {
                    if (info.msg !== 'OK') {
                        show_message(info.msg);
                    } else {
                        add_history(info.result, true);
                    }
                }
            });
            reset_panel();
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
            let name = seats[position][0];
            $("#all_players button[pos=" + position + "]").siblings("span").text(name);
        }
    }

    gid_source.addEventListener('game_info', function (event) {
        let data = JSON.parse(event.data);
        if ("seats" in data) {
            update_seats(data.seats);
        }
        if (data.cards) {
            show_message("身份牌已发放");
            $.ajax({
                url: "api/get_game_info",
                dataType: "json",
                success: function (info) {
                    $(".player > button").off("click");
                    $(".player > button").on("click", skills.select);
                    let role = info.role;
                    $("#check-role-dialog .modal-body").html(
                        '<p>' +
                        '你的身份是：' + role.role_type[1] +
                        '</p>' +
                        '<div class="role-img">' +
                        '<img src="/static/images/werewolf/cards/' + role.role_type[0].toLowerCase().replace('role_type_', '') + '.jpg"' +
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
            add_history(data.history, data.show);
        }

        if ("next_step" in data) {
            $("#next-step").text(data.next_step)
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

