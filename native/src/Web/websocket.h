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
using namespace Poco;
using namespace Poco::Net;
namespace DeepLr::Web {
	class WebServer : public HTTPRequestHandler {
	public:
		WebServer(int port = 0);
		void handleRequest(HTTPServerRequest& request, HTTPServerResponse& response);
		bool Start();
		inline bool IsConnect() {
			return isConnect;
		}
		void Close();
	private:
		std::vector<std::shared_ptr<WebSocket>> clinets;//当前连接的客户端
		std::mutex socketmtx;
		void BindReceiveAsync(const std::shared_ptr<WebSocket>& client);
		std::string GetClientIp(const std::shared_ptr<WebSocket>& client);
		std::string NormalizeIpText(std::string ip);
		int port;//端口号
		bool isConnect;
		ServerSocket socket;//套接字
		std::unique_ptr<HTTPServer> srv;
	};
	//请求处理工厂
	class RequestHandlerFactory : public HTTPRequestHandlerFactory {
	public:
		HTTPRequestHandler* createRequestHandler(const HTTPServerRequest& request) {
			return new WebServer;
		}

	};
}