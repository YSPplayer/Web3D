#include <iostream>
#include <atomic>
#include <conio.h> 
#include "Web/websocket.h"
using namespace DeepLr::Web;
std::atomic<bool> isRunning(true);
void keyboardListener() {
    while (true) {
        if (_kbhit()) {
            int key = _getch();
            if (key == 27)  // ESC
            {
                std::cout << "stop server,esc quit." << std::endl;
                isRunning.store(false);
                break;
            }
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
        }
    }
}
int main() {
    std::thread listener(keyboardListener);
    WebServer* server = new WebServer(9958);
    server->Start();
    if (listener.joinable()) listener.join();
    return 0;
}