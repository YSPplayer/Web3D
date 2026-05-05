#pragma once
#include "websocket.h"
#include "../define.h"
#include <cstdint>
#include "../data.h"
using namespace DeepLr;
namespace DeepLr::Web {
		class WebProcess {
		public:
			static bool HandelMessage(int32_t frameType,const std::shared_ptr<WebSocket>& client,const std::vector<char>& buffer);
			static bool SendMessageBinary(const std::shared_ptr<WebSocket>& client, const WebSocketPackage& package);
			static bool SendMessageBinary(const std::shared_ptr<WebSocket>& client, int32_t code);
		private:
			static bool ParseHeaderBinary(const std::shared_ptr<WebSocket>& client, const std::vector<char>& buffer, WebSocketPackage& package);
			static bool HandelMessageBinary(const std::shared_ptr<WebSocket>& client, const std::vector<char>& buffer);
			static bool MessageDebug(const std::shared_ptr<WebSocket>& client,const std::string message);
	};
}
