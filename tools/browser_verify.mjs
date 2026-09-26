import fs from "node:fs";

const targets = await fetch("http://127.0.0.1:9240/json").then(response => response.json());
const target = targets.find(item => item.type === "page" && item.url === "http://127.0.0.1:4173/");
if (!target) {
    throw new Error("未找到预览页面");
}

const socket = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((resolve, reject) => {
    socket.addEventListener("open", resolve, { once: true });
    socket.addEventListener("error", reject, { once: true });
});

let messageId = 0;
const pending = new Map();
socket.addEventListener("message", event => {
    const message = JSON.parse(event.data);
    if (message.id && pending.has(message.id)) {
        pending.get(message.id)(message);
        pending.delete(message.id);
    }
});

function send(method, params = {}) {
    messageId += 1;
    socket.send(JSON.stringify({ id: messageId, method, params }));
    return new Promise(resolve => pending.set(messageId, resolve));
}

async function evaluate(expression) {
    const response = await send("Runtime.evaluate", {
        expression,
        awaitPromise: true,
        returnByValue: true
    });
    if (response.result?.exceptionDetails) {
        throw new Error(response.result.exceptionDetails.text);
    }
    return response.result.result.value;
}

await send("Page.enable");
await send("Page.reload", { ignoreCache: true });
await new Promise(resolve => setTimeout(resolve, 700));
await evaluate(`new Promise(resolve => {
    const input = document.querySelector('#searchInput');
    input.value = 'TIM callback';
    input.dispatchEvent(new Event('input', { bubbles: true }));
    setTimeout(resolve, 350);
})`);

const callbackResult = await evaluate(`(() => {
    const cards = [...document.querySelectorAll('.function-card')];
    const targetCard = cards.find(card => card.querySelector('.function-name')?.textContent === 'HAL_TIM_PeriodElapsedCallback');
    if (targetCard) {
        targetCard.open = true;
        targetCard.scrollIntoView({ block: 'center' });
    }
    return {
        countText: document.querySelector('#resultCount')?.textContent,
        renderedCards: cards.length,
        targetFound: Boolean(targetCard),
        names: cards.slice(0, 25).map(card => card.querySelector('.function-name')?.textContent)
    };
})()`);

await new Promise(resolve => setTimeout(resolve, 250));
const detailResult = await evaluate(`(() => {
    const card = [...document.querySelectorAll('.function-card')].find(item => item.querySelector('.function-name')?.textContent === 'HAL_TIM_PeriodElapsedCallback');
    return {
        brief: card?.querySelector('.function-brief')?.textContent,
        notes: [...(card?.querySelectorAll('.detail-cell.is-wide') || [])].find(cell => cell.querySelector('h4')?.textContent === '@NOTES')?.querySelector('p')?.textContent,
        example: card?.querySelector('.example-code')?.textContent,
        detailCount: document.querySelectorAll('.function-detail').length
    };
})()`);

const screenshot = await send("Page.captureScreenshot", {
    format: "png",
    captureBeyondViewport: false
});
fs.writeFileSync(process.argv[2], Buffer.from(screenshot.result.data, "base64"));

await evaluate(`new Promise(resolve => {
    const input = document.querySelector('#searchInput');
    input.value = 'HAL';
    input.dispatchEvent(new Event('input', { bubbles: true }));
    setTimeout(resolve, 350);
})`);
const broadResult = await evaluate(`({
    countText: document.querySelector('#resultCount')?.textContent,
    renderedCards: document.querySelectorAll('.function-card').length,
    hasLoadMore: Boolean(document.querySelector('.load-more')),
    detailCount: document.querySelectorAll('.function-detail').length
})`);

await evaluate(`new Promise(resolve => {
    const input = document.querySelector('#searchInput');
    input.value = 'TIM相关的callback';
    input.dispatchEvent(new Event('input', { bubbles: true }));
    setTimeout(resolve, 350);
})`);
const naturalQueryResult = await evaluate(`({
    countText: document.querySelector('#resultCount')?.textContent,
    targetFound: [...document.querySelectorAll('.function-name')].some(item => item.textContent === 'HAL_TIM_PeriodElapsedCallback')
})`);

await evaluate(`new Promise(resolve => {
    const input = document.querySelector('#searchInput');
    input.value = '__HAL_TIM_CALC_PERIOD_DITHER';
    input.dispatchEvent(new Event('input', { bubbles: true }));
    setTimeout(() => {
        const card = [...document.querySelectorAll('.function-card')].find(item => item.querySelector('.function-name')?.textContent === '__HAL_TIM_CALC_PERIOD_DITHER');
        if (card) {
            card.open = true;
            card.scrollIntoView({ block: 'start' });
        }
        setTimeout(resolve, 200);
    }, 350);
})`);
const macroResult = await evaluate(`(() => {
    const card = [...document.querySelectorAll('.function-card')].find(item => item.querySelector('.function-name')?.textContent === '__HAL_TIM_CALC_PERIOD_DITHER');
    return {
        countText: document.querySelector('#resultCount')?.textContent,
        brief: card?.querySelector('.function-brief')?.textContent,
        params: [...(card?.querySelectorAll('.param-list li') || [])].map(item => item.textContent.trim()),
        notes: [...(card?.querySelectorAll('.detail-cell.is-wide') || [])].find(cell => cell.querySelector('h4')?.textContent === '@NOTES')?.querySelector('p')?.textContent,
        example: card?.querySelector('.example-code')?.textContent
    };
})()`);
if (process.argv[3]) {
    const macroScreenshot = await send("Page.captureScreenshot", {
        format: "png",
        captureBeyondViewport: false
    });
    fs.writeFileSync(process.argv[3], Buffer.from(macroScreenshot.result.data, "base64"));
}

await evaluate(`new Promise(resolve => {
    const input = document.querySelector('#searchInput');
    input.value = 'ADCEx Start';
    input.dispatchEvent(new Event('input', { bubbles: true }));
    setTimeout(() => {
        const names = new Set(['HAL_ADCEx_Calibration_Start', 'HAL_ADCEx_InjectedStart']);
        for (const card of document.querySelectorAll('.function-card')) {
            if (names.has(card.querySelector('.function-name')?.textContent)) {
                card.open = true;
            }
        }
        const calibration = [...document.querySelectorAll('.function-card')].find(
            card => card.querySelector('.function-name')?.textContent === 'HAL_ADCEx_Calibration_Start'
        );
        calibration?.scrollIntoView({ block: 'start' });
        setTimeout(resolve, 200);
    }, 350);
})`);
const adcResult = await evaluate(`(() => {
    const readCard = name => {
        const card = [...document.querySelectorAll('.function-card')].find(
            item => item.querySelector('.function-name')?.textContent === name
        );
        return {
            brief: card?.querySelector('.function-brief')?.textContent,
            notes: [...(card?.querySelectorAll('.detail-cell.is-wide') || [])].find(
                cell => cell.querySelector('h4')?.textContent === '@NOTES'
            )?.querySelector('p')?.textContent,
            example: card?.querySelector('.example-code')?.textContent
        };
    };
    return {
        countText: document.querySelector('#resultCount')?.textContent,
        calibration: readCard('HAL_ADCEx_Calibration_Start'),
        injectedStart: readCard('HAL_ADCEx_InjectedStart')
    };
})()`);
if (process.argv[4]) {
    const adcScreenshot = await send("Page.captureScreenshot", {
        format: "png",
        captureBeyondViewport: false
    });
    fs.writeFileSync(process.argv[4], Buffer.from(adcScreenshot.result.data, "base64"));
}

console.log(JSON.stringify({ callbackResult, detailResult, broadResult, naturalQueryResult, macroResult, adcResult }, null, 2));
socket.close();
