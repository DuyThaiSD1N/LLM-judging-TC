// state.js — Quản lý trạng thái chung của ứng dụng

let isRunning = false;

export function setRunning(running) {
    isRunning = running;
}

export function getIsRunning() {
    return isRunning;
}
