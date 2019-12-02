/*
 * @Author: Lucien Zhang
 * @Date:   2019-09-29 18:02:32
 * @Last Modified by:   Lucien Zhang
 * @Last Modified time: 2019-10-09 14:30:35
 */

// document.querySelector("#history-btn").onclick = function() { $("#history-model-content").scrollTop($("#history-model-content").prop("scrollHeight")); };
document.querySelector("#history").onfocus = function () {
    $("#history-model-content").scrollTop(this.prop("scrollHeight"));
};


// $.ajax({
//         url: "werewolf/game_process",
//         type: "GET",
//         dataType: "json",
//         success: function (data) {
//             let info=$.parseJSON(data);

//         }
//         });
