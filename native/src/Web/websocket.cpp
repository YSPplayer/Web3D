#include <string>
#include <format>
#include "websocket.h"
#include "../log.h"
namespace DeepLr::Web {
	void WebServer::BindReceiveAsync(const std::shared_ptr<WebSocket>& client) {
		if (!client) return;
		std::thread([client,this] {
			while (true) {
				bool hasclinet = false;
				{
					std::lock_guard<std::mutex> lock(socketmtx);
					auto it = std::find(clinets.begin(), clinets.end(), client);
					hasclinet = it != clinets.end();
				}
				if (hasclinet) {
					try {
						std::vector<char> full_data;
						char buffer[1024];
						int flags;
						int n;
						do {
							n = client->receiveFrame(buffer, sizeof(buffer), flags);//客户端返回消息的时候才触发，默认为阻塞状态
							if (n > 0) {
								// 将数据追加到完整消息中
								full_data.insert(full_data.end(), buffer, buffer + n);
							}
							else if (n == 0) { //客户端断开连接
								Log::Debug(std::format("client closed,ip:{}", GetClientIp(client)));
							}

						} while (n > 0 && !(flags & Poco::Net::WebSocket::FRAME_FLAG_FIN));
					}
					catch (Poco::TimeoutException& e) {
						Log::Debug(std::format("client reveive timeout.ip:{}", GetClientIp(client)));
						break;
					}
					catch (Poco::Net::WebSocketException& e) {
						Log::Debug(std::format("websocket error:{},ip:{}", e.what(), GetClientIp(client)));
						break;
					}
					catch (std::exception& e) {
						Log::Debug(std::format("websocket error:{},ip:{}", e.what(), GetClientIp(client)));
						break;
					}
				}
				else {
					Log::Debug("Client reveive error: The client does not exist.");
					break;
				}
			}
			{
				std::lock_guard<std::mutex> lock(socketmtx);
				//移除当前错误的客户端
				clinets.erase(std::remove(clinets.begin(), clinets.end(), client), clinets.end());
			}
			}).detach();
	}
	//获取到当前的ip地址
	std::string WebServer::GetClientIp(const std::shared_ptr<WebSocket>& client) {
		if (client == nullptr) return "";
		//std::string serverIp = NormalizeIpText(client->address().host().toString());
		return NormalizeIpText(client->peerAddress().host().toString());
	}
	std::string WebServer::NormalizeIpText(std::string ip) {
		const std::string mappedPrefix = "::ffff:";
		if (ip.rfind(mappedPrefix, 0) == 0 && ip.size() > mappedPrefix.size()) {
			ip = ip.substr(mappedPrefix.size());
		}
		if (ip == "localhost") {
			return "127.0.0.1";
		}
		return ip;
	}
	void WebServer::handleRequest(HTTPServerRequest& request, HTTPServerResponse& response) {
		std::string error = "";
		bool success = false;
		try {
			{
				std::lock_guard<std::mutex> lock(socketmtx);
				//新的连接来的时候触发,创建新的链接
				std::shared_ptr<WebSocket> client = std::make_shared<WebSocket>(request, response);
				Log::Debug(std::format("client connect success,ip:{}", GetClientIp(client)));
				clinets.push_back(client);
				BindReceiveAsync(client);
			}
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
	WebServer::WebServer(int port):port(port), isConnect(false), srv(nullptr){
			
	}
	//开始
	bool WebServer::Start() {
		std::string error = "";
		isConnect = false;
		try {
			socket = ServerSocket(port);
			srv = std::make_unique<HTTPServer>(new RequestHandlerFactory, socket, new HTTPServerParams);
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
		if (isConnect) srv->stop();
	}



}