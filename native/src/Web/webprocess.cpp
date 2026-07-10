#include "webprocess.h"
#include <cstring>
#include "../log.h"
namespace DeepLr::Web {
	/// <summary>
	/// 处理客户端发送的包，异步执行
	/// </summary>
	/// <param name="frameType"></param>
	/// <param name="client"></param>
	/// <param name="buffer"></param>
	/// <returns></returns>
	bool WebProcess::HandelMessage(int32_t frameType, const std::shared_ptr<WebSocket>& client, const std::vector<char>& buffer) {
		if (!client) return false;
		if (frameType == Poco::Net::WebSocket::FRAME_BINARY) {
			return HandelMessageBinary(client, buffer);
		}
		return false;
	}
	bool WebProcess::SendMessageBinary(const std::shared_ptr<WebSocket>& client, const WebSocketPackage& package) {
		if (!client) return false;
		std::vector<char> buffer;
		size_t estimatedSize = sizeof(package.version) + sizeof(package.code) +
			sizeof(package.size);
		for (int32_t i = 0; i < package.size; ++i) {
			estimatedSize += sizeof(package.length) + package.length[i];  // 长度字段 + 实际数据
		}
		//预分配内存
		buffer.reserve(estimatedSize);
		//版本号
		buffer.insert(buffer.end(),
			reinterpret_cast<const char*>(&package.version),
			reinterpret_cast<const char*>(&package.version) + sizeof(package.version)); //参数二 起始指针 参数三 结束指针
		//消息类型
		buffer.insert(buffer.end(),
			reinterpret_cast<const char*>(&package.code),
			reinterpret_cast<const char*>(&package.code) + sizeof(package.code));
		//数据流总数量
		buffer.insert(buffer.end(),
			reinterpret_cast<const char*>(&package.size),
			reinterpret_cast<const char*>(&package.size) + sizeof(package.size));
		//数据流数据
		if (package.size > 0) {
			for (int32_t i = 0; i < package.size; ++i) { 
				int32_t length = package.length[i]; //包长度
				char* context = package.context[i];//包内容
				// 安全检查
				if (!context || length <= 0) {
					Log::Debug("Invalid data block.");
					return false;
				}
				//先插入长度
				buffer.insert(buffer.end(),
					reinterpret_cast<const char*>(&length),
					reinterpret_cast<const char*>(&length) + sizeof(length));
				//再插入内容
				buffer.insert(buffer.end(),
					reinterpret_cast<const char*>(context),
					reinterpret_cast<const char*>(context) + length);
			}
		}
		client->sendFrame(buffer.data(), buffer.size(), Poco::Net::WebSocket::FRAME_BINARY);
		return true;
	}

	bool WebProcess::SendMessageBinary(const std::shared_ptr<WebSocket>& client, int32_t code) {
		WebSocketPackage package;
		package.version = SERVER_VERSION;
		package.code = code;
		package.size = 0;
		package.length = nullptr;
		package.context = nullptr;
		return SendMessageBinary(client, package);
	}

	bool WebProcess::ParseHeaderBinary(const std::shared_ptr<WebSocket>& client, const std::vector<char>& buffer, WebSocketPackage& package) {
		if (buffer.size() < sizeof(package.version)) {
			MessageDebug(client,"Header Binary Data format error.The data size is incorrect.");
			return false;
		}
		int offset = 0;
		//version
		std::memcpy(&package.version, buffer.data(), sizeof(package.version));
		if (package.version != SERVER_VERSION) {
			MessageDebug(client,std::format("Server and client versions do not match,server version:{},client version:{}", SERVER_VERSION, package.version));
			return false;
		}
		offset += sizeof(package.version);
		if (buffer.size() < offset + sizeof(package.code)) {
			MessageDebug(client, "Header Binary Data format error.The data size is incorrect.");
			return false;
		}
		std::memcpy(&package.code, buffer.data() + offset, sizeof(package.code));
		offset += sizeof(package.code);
		return true;
	}

	bool WebProcess::HandelMessageBinary(const std::shared_ptr<WebSocket>& client, const std::vector<char>& buffer) {
		WebSocketPackage package;
		bool success = ParseHeaderBinary(client, buffer,package);
		if (!success) return false;
		Log::Debug(std::format("Received client message,code:{}", package.code));
		//解析Code
		switch (package.code)
		{
		case CLIENT_TO_SERVER_HEART_BEAT: { //心跳机制
			SendMessageBinary(client, SERVER_TO_CLIENT_HEART_BEAT);
		}
			break;
		default:
			break;
		}
		return true;
	}
	bool WebProcess::MessageDebug(const std::shared_ptr<WebSocket>& client, const std::string message) {
		Log::Debug(message);
		return true;
	}
}
