#include <iostream>
#include <atomic>
#include <thread>
#include <chrono>
#include <conio.h> 
#include "Web/websocket.h"
using namespace DeepLr::Web;
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
int main() {
    server = new WebServer(9958);
    server->Start();
    std::thread listener(keyboardListener);
    if (listener.joinable()) listener.join();
    return 0;
}
