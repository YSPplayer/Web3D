#pragma once
#include <Poco/Net/HTTPServer.h>
#include <Poco/Net/HTTPRequestHandler.h>
#include <Poco/Net/HTTPRequestHandlerFactory.h>
#include <Poco/Net/HTTPServerRequest.h>
#include <Poco/Net/HTTPServerResponse.h>
#include <Poco/Net/WebSocket.h>
#include <Poco/Net/ServerSocket.h>
#include <Poco/Net/NetException.h>
#include <iostream>
#include <string>
#include <vector>
#include <mutex>
#include <memory>
using namespace Poco;
using namespace Poco::Net;
namespace DeepLr::Web {
	struct WebSocketContext {
		std::vector<std::shared_ptr<WebSocket>> clients;//当前连接的客户端
		std::mutex clientsMutex;
	};

	class WebSocketHandler final : public HTTPRequestHandler {
	public:
		explicit WebSocketHandler(std::shared_ptr<WebSocketContext> context);
		void handleRequest(HTTPServerRequest& request, HTTPServerResponse& response) override;
	private:
		std::shared_ptr<WebSocketContext> context;
		void BindReceiveAsync(const std::shared_ptr<WebSocket>& client);
		static bool HasClient(const std::shared_ptr<WebSocketContext>& context, const std::shared_ptr<WebSocket>& client);
		static void RemoveClient(const std::shared_ptr<WebSocketContext>& context, const std::shared_ptr<WebSocket>& client);
		static std::string GetClientIp(const std::shared_ptr<WebSocket>& client);
		static std::string NormalizeIpText(std::string ip);
	};

	//请求处理工厂
	class RequestHandlerFactory final : public HTTPRequestHandlerFactory {
	public:
		explicit RequestHandlerFactory(std::shared_ptr<WebSocketContext> context);
		HTTPRequestHandler* createRequestHandler(const HTTPServerRequest& request) override;
	private:
		std::shared_ptr<WebSocketContext> context;
	};

	class WebServer {
	public:
		WebServer(int port = 0);
		bool Start();
		inline bool IsConnect() const {
			return isConnect;
		}
		void Close();
	private:
		int port;//端口号
		bool isConnect;
		ServerSocket socket;//套接字
		std::unique_ptr<HTTPServer> srv;
		std::shared_ptr<WebSocketContext> context;
	};
}
