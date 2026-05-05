#pragma once
#include <iostream>
#include <string>
namespace DeepLr {
	class Log {
		Log() = default;
	public:
		static void Debug(const std::string& msg) {
			std::cout << msg << std::endl;
		}
	};
}

