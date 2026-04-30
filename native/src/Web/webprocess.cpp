#include "webprocess.h"
namespace DeepLr::Web {
	bool WebProcess::SendBinaryMessage(const std::shared_ptr<WebSocket>& client, int32_t code) {
		if (!client) return false;
		int32_t version = SERVER_VERSION;
		std::vector<char> buffer;
		buffer.resize(sizeof(version) + sizeof(code));
		int32_t offest = 0;
		std::memcpy(buffer.data(), &version,sizeof(version));
		offest += sizeof(version);
		std::memcpy(buffer.data() + offest, &code, sizeof(code));
		offest += sizeof(code);
		client->sendFrame(buffer.data(), buffer.size(), Poco::Net::WebSocket::FRAME_BINARY);
	}
}