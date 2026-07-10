#include "log.h"

#include <condition_variable>
#include <chrono>
#include <ctime>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <mutex>
#include <queue>
#include <sstream>
#include <thread>

#ifdef _WIN32
#include <windows.h>
#endif

namespace DeepLr {
	namespace {
		std::filesystem::path ResolveLogPath() {
#ifdef _WIN32
			wchar_t buffer[MAX_PATH] = {};
			DWORD length = GetModuleFileNameW(nullptr, buffer, MAX_PATH);
			if (length > 0 && length < MAX_PATH) {
				return std::filesystem::path(buffer).parent_path() / "message.log";
			}
#endif
			return std::filesystem::current_path() / "message.log";
		}

		std::string NowText() {
			auto now = std::chrono::system_clock::now();
			std::time_t time = std::chrono::system_clock::to_time_t(now);
			std::tm localTime {};
#ifdef _WIN32
			localtime_s(&localTime, &time);
#else
			localtime_r(&time, &localTime);
#endif
			std::ostringstream stream;
			stream << std::put_time(&localTime, "%Y-%m-%d %H:%M:%S");
			return stream.str();
		}

		class AsyncLogWriter {
		public:
			AsyncLogWriter()
				: done(false), output(ResolveLogPath(), std::ios::app), worker(&AsyncLogWriter::Run, this) {}

			~AsyncLogWriter() {
				Shutdown();
			}

			void Write(const std::string& msg) {
				std::string line = "[" + NowText() + "] " + msg;
				{
					std::lock_guard<std::mutex> lock(consoleMutex);
					std::cout << msg << std::endl;
				}
				{
					std::lock_guard<std::mutex> lock(queueMutex);
					messages.push(std::move(line));
				}
				condition.notify_one();
			}

			void Shutdown() {
				{
					std::lock_guard<std::mutex> lock(queueMutex);
					if (done) return;
					done = true;
				}
				condition.notify_one();
				if (worker.joinable()) {
					worker.join();
				}
				if (output.is_open()) {
					output.flush();
					output.close();
				}
			}

		private:
			void Run() {
				for (;;) {
					std::queue<std::string> pending;
					{
						std::unique_lock<std::mutex> lock(queueMutex);
						condition.wait(lock, [&] {
							return done || !messages.empty();
						});
						pending.swap(messages);
					}
					while (!pending.empty()) {
						if (output.is_open()) {
							output << pending.front() << '\n';
						}
						pending.pop();
					}
					if (output.is_open()) {
						output.flush();
					}
					{
						std::lock_guard<std::mutex> lock(queueMutex);
						if (done && messages.empty()) {
							break;
						}
					}
				}
			}

			bool done;
			std::ofstream output;
			std::thread worker;
			std::mutex queueMutex;
			std::mutex consoleMutex;
			std::condition_variable condition;
			std::queue<std::string> messages;
		};

		AsyncLogWriter& Writer() {
			static AsyncLogWriter writer;
			return writer;
		}
	}

	void Log::Debug(const std::string& msg) {
		//Writer().Write(msg);
		std::cout << msg << std::endl;
	}

	void Log::Shutdown() {
		Writer().Shutdown();
	}
}
