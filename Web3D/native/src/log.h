#pragma once
#include <string>
namespace DeepLr {
	class Log {
		Log() = default;
	public:
		static void Debug(const std::string& msg);
		static void Shutdown();
	};
}
