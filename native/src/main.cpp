#include <iostream>
#include <atomic>
#include <thread>
#include <chrono>
#include <conio.h> 
#include "Web/websocket.h"
#include "Neural/neural.h"
#include "Neural/sample.h"
using namespace DeepLr::Web;
using namespace DeepLr::Neural;
//std::atomic<bool> isRunning(true);
WebServer* server = nullptr;
void keyboardListener() {
    while (true) {
        if (_kbhit()) {
            int key = _getch();
            if (key == 27)  // ESC
            {
                std::cout << "stop server,esc quit." << std::endl;
                //isRunning.store(false);
                if(server) server->Close();
                break;
            }
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }
}
void TestTrain() {
    std::vector<std::shared_ptr<Sample>> samples = Sample::Load("D:/YueShaoPu/trainimg2");
    const std::shared_ptr<Neural>& neural = Neural::BuildDefaultNeural();
    neural->Train(samples,150);
}
int main() {
    server = new WebServer(9958);
    server->Start();
    std::thread listener(keyboardListener);
    TestTrain();
    if (listener.joinable()) listener.join();
    return 0;
}
