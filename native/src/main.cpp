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
void Predict() {
   // const std::shared_ptr<Neural>& neural = std::make_shared<Neural>();
   // neural->InitFromModel("D:/YueShaoPu/trainimg2/Model/2026_5_19.dlm");
   // std::array<int32_t, 4> array;
   ///* std::shared_ptr<Sample> sample = Sample::Load("D:/YueShaoPu/trainimg2/8382.png", "8382");
   // Tensor3D output;*/
   // //neural->Predict(*sample->Data(), array, output);
   // std::vector<std::string> files = Sample::GetPngFiles("D:/YueShaoPu/trainimg2");
   // neural->Validate(files);
}
void Train() {
    std::vector<std::string> files = Sample::GetPngFiles("D:/YueShaoPu/trainimg");
    const std::shared_ptr<Neural>& neural = std::make_shared<Neural>();
    neural->InitFromModel("D:/YueShaoPu/trainimg2/Model/2026_5_19.dlm");
    neural->Train("D:/YueShaoPu/trainimg2/Model/2026_5_19.dlm",files,100,64);
}
int main() {
    server = new WebServer(9958);
    server->Start();
    std::thread listener(keyboardListener);
    Train();
    //Predict();
    if (listener.joinable()) listener.join();
    return 0;
}
