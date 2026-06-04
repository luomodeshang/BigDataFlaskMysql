// 全局变量
let currentProtocol = 'usb';
let updateIntervals = {};
let packetCounters = {
    usb: { sent: 0, received: 0, lost: 0 },
    tcp: { sent: 0, acked: 0, retrans: 0 },
    udp: { sent: 0, received: 0, lost: 0 },
    modbus: { requests: 0, responses: 0 }
};

// 页面导航
function initNavigation() {
    const navButtons = document.querySelectorAll('.nav-btn');
    
    navButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const protocol = btn.dataset.protocol;
            switchProtocol(protocol);
        });
    });
}

function switchProtocol(protocol) {
    // 停止当前协议的更新
    if (updateIntervals[currentProtocol]) {
        clearInterval(updateIntervals[currentProtocol]);
    }
    
    // 清空当前页面的动画
    clearProtocolAnimations(currentProtocol);
    
    // 更新导航按钮
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.protocol === protocol);
    });
    
    // 切换页面
    document.querySelectorAll('.protocol-page').forEach(page => {
        page.classList.toggle('active', page.id === `${protocol}-page`);
    });
    
    currentProtocol = protocol;
    
    // 重置计数器
    resetCounters(protocol);
    
    // 开始新协议的演示
    startProtocolDemo(protocol);
}

function clearProtocolAnimations(protocol) {
    const lanes = {
        usb: document.getElementById('usb-lane'),
        tcp: document.getElementById('tcp-lane'),
        udp: document.getElementById('udp-lane'),
        modbus: document.getElementById('modbus-lane')
    };
    
    if (lanes[protocol]) {
        lanes[protocol].innerHTML = '';
    }
}

function resetCounters(protocol) {
    if (packetCounters[protocol]) {
        Object.keys(packetCounters[protocol]).forEach(key => {
            packetCounters[protocol][key] = 0;
        });
    }
}

// 开始协议演示
function startProtocolDemo(protocol) {
    switch(protocol) {
        case 'usb':
            startUSBDemo();
            break;
        case 'tcp':
            startTCPDemo();
            break;
        case 'udp':
            startUDPDemo();
            break;
        case 'modbus':
            startMODBUSDemo();
            break;
    }
}

// USB演示 - 连续稳定数据流
function startUSBDemo() {
    const lane = document.getElementById('usb-lane');
    const sourceQueue = document.getElementById('usb-source-queue');
    const receivedCount = document.getElementById('usb-received-count');
    
    // 创建数据包队列
    function createPacketInQueue() {
        const packet = document.createElement('div');
        packet.className = 'data-packet';
        packet.textContent = 'D';
        sourceQueue.appendChild(packet);
        
        // 限制队列长度
        if (sourceQueue.children.length > 5) {
            sourceQueue.removeChild(sourceQueue.firstChild);
        }
    }
    
    // 发送数据包
    function sendPacket() {
        // 从队列移除
        if (sourceQueue.firstChild) {
            sourceQueue.removeChild(sourceQueue.firstChild);
        }
        
        // 创建移动的数据包
        const packet = document.createElement('div');
        packet.className = 'moving-packet';
        packet.textContent = 'DATA';
        lane.appendChild(packet);
        
        packetCounters.usb.sent++;
        
        // 数据包到达后
        setTimeout(() => {
            packet.remove();
            packetCounters.usb.received++;
            receivedCount.textContent = packetCounters.usb.received;
            updateUSBStats();
        }, 2000);
    }
    
    // 定期创建和发送
    setInterval(createPacketInQueue, 500);
    updateIntervals.usb = setInterval(sendPacket, 800);
    
    // 立即开始
    createPacketInQueue();
    setTimeout(sendPacket, 500);
}

function updateUSBStats() {
    document.getElementById('usb-speed').textContent = '4800';
    document.getElementById('usb-total').textContent = packetCounters.usb.sent;
    document.getElementById('usb-lost').textContent = '0';
    document.getElementById('usb-latency').textContent = '2';
}

// TCP演示 - 可靠传输
function startTCPDemo() {
    const lane = document.getElementById('tcp-lane');
    const sourceQueue = document.getElementById('tcp-source-queue');
    const waitingAcks = document.getElementById('tcp-waiting-acks');
    const ackSending = document.getElementById('tcp-ack-sending');
    const receivedCount = document.getElementById('tcp-received-count');
    
    let seqNum = 1001;
    const waitingPackets = new Map();
    
    function createPacketInQueue() {
        const packet = document.createElement('div');
        packet.className = 'data-packet';
        packet.textContent = seqNum;
        sourceQueue.appendChild(packet);
        
        if (sourceQueue.children.length > 3) {
            sourceQueue.removeChild(sourceQueue.firstChild);
        }
    }
    
    function sendPacket() {
        if (sourceQueue.firstChild) {
            sourceQueue.removeChild(sourceQueue.firstChild);
        }
        
        const packet = document.createElement('div');
        packet.className = 'moving-packet';
        packet.textContent = `#${seqNum}`;
        packet.style.top = '20px';
        lane.appendChild(packet);
        
        packetCounters.tcp.sent++;
        
        // 添加到等待确认列表
        const waitingPacket = document.createElement('div');
        waitingPacket.className = 'waiting-packet';
        waitingPacket.textContent = seqNum;
        waitingAcks.appendChild(waitingPacket);
        waitingPackets.set(seqNum, waitingPacket);
        
        // 数据包到达，发送ACK
        setTimeout(() => {
            packet.remove();
            packetCounters.tcp.received++;
            receivedCount.textContent = packetCounters.tcp.received;
            
            // 发送ACK
            const ack = document.createElement('div');
            ack.className = 'ack-packet';
            ack.textContent = `ACK${seqNum}`;
            ack.style.top = '60px';
            lane.appendChild(ack);
            
            // ACK到达，移除等待
            setTimeout(() => {
                ack.remove();
                if (waitingPackets.has(seqNum)) {
                    waitingPackets.get(seqNum).remove();
                    waitingPackets.delete(seqNum);
                    packetCounters.tcp.acked++;
                }
                updateTCPStats();
            }, 2000);
        }, 2000);
        
        seqNum++;
    }
    
    // 模拟偶尔重传
    function simulateRetransmission() {
        if (waitingPackets.size > 0 && Math.random() < 0.1) {
            const retransSeq = Array.from(waitingPackets.keys())[0];
            const retransPacket = document.createElement('div');
            retransPacket.className = 'moving-packet retrans-packet';
            retransPacket.textContent = `#${retransSeq}(重传)`;
            retransPacket.style.top = '20px';
            lane.appendChild(retransPacket);
            
            packetCounters.tcp.retrans++;
            
            setTimeout(() => {
                retransPacket.remove();
            }, 2000);
        }
    }
    
    setInterval(createPacketInQueue, 600);
    updateIntervals.tcp = setInterval(() => {
        sendPacket();
        setTimeout(simulateRetransmission, 1000);
    }, 2500);
    
    createPacketInQueue();
    setTimeout(sendPacket, 500);
}

function updateTCPStats() {
    document.getElementById('tcp-sent').textContent = packetCounters.tcp.sent;
    document.getElementById('tcp-acked').textContent = packetCounters.tcp.acked;
    document.getElementById('tcp-retrans').textContent = packetCounters.tcp.retrans;
    const reliability = packetCounters.tcp.sent > 0 
        ? ((packetCounters.tcp.acked / packetCounters.tcp.sent) * 100).toFixed(1)
        : 100;
    document.getElementById('tcp-reliability').textContent = reliability + '%';
}

// UDP演示 - 快速但可能丢包
function startUDPDemo() {
    const lane = document.getElementById('udp-lane');
    const sourceQueue = document.getElementById('udp-source-queue');
    const lostArea = document.getElementById('udp-lost-area');
    const receivedCount = document.getElementById('udp-received-count');
    
    let packetId = 1;
    const lossRate = 0.15; // 15%丢包率
    
    function createPacketInQueue() {
        const packet = document.createElement('div');
        packet.className = 'data-packet';
        packet.textContent = packetId;
        sourceQueue.appendChild(packet);
        
        if (sourceQueue.children.length > 4) {
            sourceQueue.removeChild(sourceQueue.firstChild);
        }
    }
    
    function sendPacket() {
        if (sourceQueue.firstChild) {
            sourceQueue.removeChild(sourceQueue.firstChild);
        }
        
        const packet = document.createElement('div');
        packet.className = 'moving-packet';
        packet.textContent = `#${packetId}`;
        packet.style.top = '20px';
        lane.appendChild(packet);
        
        packetCounters.udp.sent++;
        
        // 判断是否丢包
        const willLost = Math.random() < lossRate;
        
        if (willLost) {
            packet.classList.add('lost');
            packetCounters.udp.lost++;
            
            // 添加到丢失区域
            setTimeout(() => {
                const lostPacket = document.createElement('div');
                lostPacket.className = 'lost-packet';
                lostPacket.textContent = packetId;
                lostArea.appendChild(lostPacket);
                
                // 限制丢失区域显示数量
                if (lostArea.children.length > 10) {
                    lostArea.removeChild(lostArea.firstChild.nextSibling);
                }
            }, 750);
        } else {
            // 成功接收
            setTimeout(() => {
                packet.remove();
                packetCounters.udp.received++;
                receivedCount.textContent = packetCounters.udp.received;
                updateUDPStats();
            }, 1500);
        }
        
        // 无论是否丢失都移除动画元素
        if (!willLost) {
            setTimeout(() => packet.remove(), 1500);
        } else {
            setTimeout(() => packet.remove(), 1500);
        }
        
        packetId++;
    }
    
    setInterval(createPacketInQueue, 400);
    updateIntervals.udp = setInterval(sendPacket, 600);
    
    createPacketInQueue();
    setTimeout(sendPacket, 300);
}

function updateUDPStats() {
    document.getElementById('udp-sent').textContent = packetCounters.udp.sent;
    document.getElementById('udp-received-stat').textContent = packetCounters.udp.received;
    document.getElementById('udp-lost').textContent = packetCounters.udp.lost;
    const lossRate = packetCounters.udp.sent > 0
        ? ((packetCounters.udp.lost / packetCounters.udp.sent) * 100).toFixed(1)
        : 0;
    document.getElementById('udp-loss-rate').textContent = lossRate + '%';
}

// MODBUS演示 - 主从请求响应
function startMODBUSDemo() {
    const lane = document.getElementById('modbus-lane');
    const requestQueue = document.getElementById('modbus-requests');
    const slaves = [1, 2, 3];
    let requestId = 1;
    
    function createRequest() {
        const request = document.createElement('div');
        request.className = 'request-item';
        request.textContent = `请求#${requestId}`;
        requestQueue.appendChild(request);
        
        if (requestQueue.children.length > 3) {
            requestQueue.removeChild(requestQueue.firstChild.nextSibling);
        }
    }
    
    function sendRequest() {
        if (requestQueue.firstChild && requestQueue.firstChild.nextSibling) {
            requestQueue.removeChild(requestQueue.firstChild.nextSibling);
        }
        
        // 随机选择一个从站
        const slaveId = slaves[Math.floor(Math.random() * slaves.length)];
        const slaveEl = document.querySelector(`.slave-device[data-id="${slaveId}"]`);
        const statusEl = document.getElementById(`slave${slaveId}-status`);
        const dataEl = document.getElementById(`slave${slaveId}-data`);
        
        // 发送请求
        const request = document.createElement('div');
        request.className = 'modbus-request';
        request.textContent = `请求#${requestId}`;
        request.style.top = '20px';
        lane.appendChild(request);
        
        packetCounters.modbus.requests++;
        
        // 更新从站状态
        if (slaveEl) {
            slaveEl.classList.add('active');
            statusEl.textContent = '处理请求中...';
        }
        
        // 请求到达从站
        setTimeout(() => {
            request.style.left = '50%';
            
            // 从站响应
            setTimeout(() => {
                const response = document.createElement('div');
                response.className = 'modbus-response';
                response.textContent = `响应#${requestId}`;
                response.style.top = '60px';
                response.style.right = '50%';
                lane.appendChild(response);
                
                // 更新从站数据
                const registerValue = Math.floor(Math.random() * 65535);
                dataEl.textContent = `寄存器值: ${registerValue}`;
                
                // 响应到达主站
                setTimeout(() => {
                    response.style.right = '-90px';
                    packetCounters.modbus.responses++;
                    updateMODBUSStats();
                    
                    if (slaveEl) {
                        slaveEl.classList.remove('active');
                        statusEl.textContent = '等待请求';
                    }
                    
                    setTimeout(() => {
                        request.remove();
                        response.remove();
                    }, 3000);
                }, 1500);
            }, 500);
        }, 2000);
        
        requestId++;
    }
    
    setInterval(createRequest, 2000);
    updateIntervals.modbus = setInterval(sendRequest, 3500);
    
    createRequest();
    setTimeout(sendRequest, 1000);
}

function updateMODBUSStats() {
    document.getElementById('modbus-requests-total').textContent = packetCounters.modbus.requests;
    document.getElementById('modbus-responses-total').textContent = packetCounters.modbus.responses;
    document.getElementById('modbus-response-time').textContent = '25';
}

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    // 确保body可见
    if (document.body) {
        document.body.classList.add('loaded');
    }
    
    initNavigation();
    startProtocolDemo(currentProtocol);
});

// 备用方案：如果DOMContentLoaded已经触发，直接添加loaded类
if (document.body) {
    document.body.classList.add('loaded');
}
