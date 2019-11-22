/*
 * @Author: Lucien Zhang
 * @Date:   2019-10-04 19:57:26
 * @Last Modified by:   Lucien Zhang
 * @Last Modified time: 2019-10-16 17:49:34
 */
var Queue = (() => {
    const map = new WeakMap();
    let _items = []
    class Queue {
        constructor(...items) {
            //initialize the items in queue
            map.set(this, []);
            _items = map.get(this);
            // enqueuing the items passed to the constructor
            this.enqueue(...items)
        }

        enqueue(...items) {
            //push items into the queue
            this._items = [...this._items, ...items]
            return this._items;
        }

        dequeue(count = 1) {
            //pull out the first item from the queue
            _items.splice(0, count);
            return this._items;
        }

        peek() {
            //peek at the first item from the queue
            return _items[0]
        }

        size() {
            //get the length of queue
            return _items.length
        }

        isEmpty() {
            //find whether the queue is empty or no
            return _items.length === 0
        }

        toArray() {
            return _items
        }

    }
    return Queue
})()

let audio_status = 'waiting';


// let my_queue = new Queue(1,24,4);
// // [1, 24, 4]
// my_queue.enqueue(23)
// //[1, 24, 4, 23]
// my_queue.enqueue(1,2,342);
// //[1, 24, 4, 23, 1, 2, 342]
// my_queue.dequeue();
// //[24, 4, 23, 1, 2, 342]
// my_queue.dequeue(3)
// //[1, 2, 342]
// my_queue.isEmpty()
// // false
// my_queue.size();
// //3
// my_queue.toArray();
// //[1, 2, 342]

let back_audio = document.querySelector("#back_audio");
let step_audio = document.querySelector("#step_audio");
let game_status = 'DAY';
let audio_queue = new Queue();
let toget = 0;

// setInterval(function(){

// },1000);



// get audio list
setInterval($.ajax({
    url: "werewolf/get_game_info?content=audio&toget=" + toget,
    type: "GET",
    dataType: "json",
    success: function(data) {
        let info = JSON.parse(data);
        if (info.length > 0) {
            audio_queue.enqueue(...info);
            toget += info.length;
        }
    }
}), 500);

//play audio list
setInterval(function() {
    if (step_audio.paused || !audio_queue.isEmpty()) {
        step_audio.src = audio_queue.peek();
        audio_queue.dequeue();
        step_audio.play()
    }
}, 500);
