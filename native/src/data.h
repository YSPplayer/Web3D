#pragma once
#include <stdint.h>
#include <algorithm>
namespace DeepLr {
	struct Point2D {
		int32_t x;
		int32_t y;
	};
	struct Kernel {
		int32_t k{0};//卷积核尺寸
		int32_t pad{0};//填充
		int32_t stride{0};//步长
		float** data{nullptr};//卷积核数据
		Kernel& operator=(Kernel&& other) noexcept {
			if (this != &other) {
				//释放当前资源
				if (data != nullptr) {
					for (int32_t i = 0; i < k; ++i) {
						delete[] data[i];
					}
					delete[] data;
				}
				k = other.k;
				pad = other.pad;
				stride = other.stride;
				data = other.data;
				other.k = 0;
				other.pad = 0;
				other.stride = 0;
				other.data = nullptr;
			}
			return *this;
		}
		Kernel& operator=(const Kernel& other) {
			if (this != &other) {
				float** newData = nullptr;
				try {
					if (other.data != nullptr) {
						newData = new float* [other.k];
						for (int32_t i = 0; i < other.k; ++i) {
							newData[i] = new float[other.k]();
							for (int32_t j = 0; j < other.k; ++j) {
								newData[i][j] = other.data[i][j];
							}
						}
					}
					if (data != nullptr) {
						for (int32_t i = 0; i < k; ++i) {
							delete[] data[i];
						}
						delete[] data;
					}
					k = other.k;
					pad = other.pad;
					stride = other.stride;
					data = newData;
				}
				catch (...) {
					if (newData != nullptr) {
						for (int32_t i = 0; i < other.k; ++i) {
							delete[] newData[i];
						}
						delete[] newData;
					}
					throw; 
				}
			}
			return *this;
		}
		Kernel(int32_t k, int32_t pad, int32_t stride) noexcept :k(k), pad(pad), stride(stride) {
			data = new float*[k];
			for (int32_t i = 0; i < k; ++i) {
				data[i] = new float[k]();
			}
		}
		Kernel() noexcept {}
		~Kernel() {
			if (data) {
				for (int32_t i = 0; i < k; ++i) {
					delete[] data[i];
					data[i] = nullptr;
				}
				delete[] data;
				data = nullptr;
			}
		}
	};
	struct WebSocketPackage {
		int32_t version;//版本号
		int32_t code;//信息类型
		int32_t size;//总的信息数量，需要解析多少次
		int32_t* length;//实际内容长度
		char** context;//实际数据内容
		WebSocketPackage(int32_t version, int32_t code, int32_t size
		, int32_t* length, char** context):version(version),code(code),size(size), length(length), context(context){

		}
		WebSocketPackage() {
			version = 0;
			code = 0;
			size = 0;
			length = nullptr;
			context = nullptr;
		}
		WebSocketPackage(const WebSocketPackage& other)
			: version(other.version), code(other.code), size(other.size) {

			// 深拷贝 length 数组
			if (other.size > 0 && other.length != nullptr) {
				length = new int32_t[other.size];
				std::copy(other.length, other.length + other.size, length);
			}
			else {
				length = nullptr;
			}
			context = nullptr;
			//if (other.size > 0 && other.context != nullptr) {
			//	// 计算总大小
			//	int32_t totalSize = 0;
			//	for (int i = 0; i < other.size; ++i) {
			//		totalSize += other.length[i];
			//	}

			//	context = new char[totalSize];
			//	std::copy(other.context, other.context + totalSize, context);
			//}
			//else {
			//	context = nullptr;
			//}
		}

		WebSocketPackage(WebSocketPackage&& other) noexcept
			: version(other.version), code(other.code), size(other.size),
			length(other.length), context(other.context) {
			other.length = nullptr;
			other.context = nullptr;
			other.size = 0;
		}
		WebSocketPackage& operator=(const WebSocketPackage& other) {
			if (this == &other) {
				return *this;  // 自赋值检查
			}
			version = other.version;
			code = other.code;
			size = other.size;
			length = other.length;
			context = other.context;
		}
		~WebSocketPackage() {
		
		}
	};

}