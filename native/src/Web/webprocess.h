#include "websocket.h"
#include "../define.h"
namespace DeepLr::Web {
		class WebProcess {
		public:
			static bool SendBinaryMessage(const std::shared_ptr<WebSocket>& client, int32_t code);
	};
}