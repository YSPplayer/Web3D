#include <string>
#include <format>
#include <algorithm>
#include <thread>
#include <utility>
#include "websocket.h"
#include "../log.h"
#include "webprocess.h"
namespace DeepLr::Web {
	WebSocketHandler::WebSocketHandler(std::shared_ptr<WebSocketContext> context):context(std::move(context)) {

	}

	void WebSocketHandler::BindReceiveAsync(const std::shared_ptr<WebSocket>& client) {
		if (!client) return;
		auto ctx = context;
		std::thread([ctx, client] {
			while (true) {
				if (WebSocketHandler::HasClient(ctx, client)) {
					try {
						std::vector<char> full_data;
						char buffer[1024];
						int flags = 0;
						int n;
						do {
							n = client->receiveFrame(buffer, sizeof(buffer), flags);//客户端返回消息的时候才触发，默认为阻塞状态
							if (n > 0) {
								// 将数据追加到完整消息中
								full_data.insert(full_data.end(), buffer, buffer + n);
							}
							else if (n == 0) { //客户端断开连接
								Log::Debug(std::format("client closed,ip:{}", WebSocketHandler::GetClientIp(client)));
								break;
							}

						} while (n > 0 && !(flags & Poco::Net::WebSocket::FRAME_FLAG_FIN));
						if (n <= 0) {
							break;
						}
						int frameType = flags & Poco::Net::WebSocket::FRAME_OP_BITMASK;
						WebProcess::HandelMessage(frameType,client, full_data);
					}
					catch (Poco::TimeoutException& e) {
						Log::Debug(std::format("client reveive timeout.ip:{}", WebSocketHandler::GetClientIp(client)));
						break;
					}
					catch (Poco::Net::WebSocketException& e) {
						Log::Debug(std::format("websocket error:{},ip:{}", e.what(), WebSocketHandler::GetClientIp(client)));
						break;
					}
					catch (std::exception& e) {
						Log::Debug(std::format("websocket error:{},ip:{}", e.what(), WebSocketHandler::GetClientIp(client)));
						break;
					}
				}
				else {
					Log::Debug("Client reveive error: The client does not exist.");
					break;
				}
			}
			WebSocketHandler::RemoveClient(ctx, client);
			}).detach();
	}

	bool WebSocketHandler::HasClient(const std::shared_ptr<WebSocketContext>& context, const std::shared_ptr<WebSocket>& client) {
		if (!context || !client) return false;
		std::lock_guard<std::mutex> lock(context->clientsMutex);
		return std::find(context->clients.begin(), context->clients.end(), client) != context->clients.end();
	}

	void WebSocketHandler::RemoveClient(const std::shared_ptr<WebSocketContext>& context, const std::shared_ptr<WebSocket>& client) {
		if (!context || !client) return;
		std::lock_guard<std::mutex> lock(context->clientsMutex);
		context->clients.erase(std::remove(context->clients.begin(), context->clients.end(), client), context->clients.end());
	}

	//获取到当前的ip地址
	std::string WebSocketHandler::GetClientIp(const std::shared_ptr<WebSocket>& client) {
		if (client == nullptr) return "";
		//std::string serverIp = NormalizeIpText(client->address().host().toString());
		return NormalizeIpText(client->peerAddress().host().toString());
	}
	std::string WebSocketHandler::NormalizeIpText(std::string ip) {
		const std::string mappedPrefix = "::ffff:";
		if (ip.rfind(mappedPrefix, 0) == 0 && ip.size() > mappedPrefix.size()) {
			ip = ip.substr(mappedPrefix.size());
		}
		if (ip == "localhost") {
			return "127.0.0.1";
		}
		return ip;
	}
	void WebSocketHandler::handleRequest(HTTPServerRequest& request, HTTPServerResponse& response) {
		std::string error = "";
		bool success = false;
		try {
			//新的连接来的时候触发,创建新的链接
			std::shared_ptr<WebSocket> client = std::make_shared<WebSocket>(request, response);
			Log::Debug(std::format("client connect success,ip:{}", GetClientIp(client)));
			{
				std::lock_guard<std::mutex> lock(context->clientsMutex);
				context->clients.push_back(client);
			}
			BindReceiveAsync(client);
			success = true;
		}
		catch (WebSocketException& exc) {
			error = exc.displayText();
		}
		catch (std::exception& exc) {
			error = exc.what();
		}
		if (!success) Log::Debug(std::format("Client connect error: {}", error));
	}

	RequestHandlerFactory::RequestHandlerFactory(std::shared_ptr<WebSocketContext> context):context(std::move(context)) {

	}

	HTTPRequestHandler* RequestHandlerFactory::createRequestHandler(const HTTPServerRequest& request) {
		return new WebSocketHandler(context);
	}

	WebServer::WebServer(int port):port(port), isConnect(false), srv(nullptr), context(std::make_shared<WebSocketContext>()){
			
	}
	//开始
	bool WebServer::Start() {
		std::string error = "";
		isConnect = false;
		try {
			socket = ServerSocket(port);
			srv = std::make_unique<HTTPServer>(new RequestHandlerFactory(context), socket, new HTTPServerParams);
			srv->start();
			isConnect = true;
		}
		catch (Exception& exc) {
			error = exc.displayText();
		}
		catch (std::exception& exc) {
			error = exc.what();
		}
		catch (...) {
		
		}
		Log::Debug(isConnect ? std::format("WebSocket listen success! port:{}",port) : std::format("WebSocket listen error:{}", error));
		return isConnect;
	}
	void WebServer::Close() {
		if (isConnect && srv) {
			srv->stop();
			isConnect = false;
		}
	}



}
