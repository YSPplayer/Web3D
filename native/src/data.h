#pragma once
#include <stdint.h>
#include <algorithm>
namespace DeepLr {
#define KEY_MAGIC "DLRMODL"
#define KEY_VERSION 1
#define KEY_TYPE_MODEL 0
#define KEY_TYPE_CHECKPOINT 1
	enum NeuralType {
		Null,
		Conv2D,//卷积
		RelU,
		MaxPool,//池化
		Flatten,//展平
		Linear,//线性
		SoftMax,//
		HeightPool,//高度池化
		FeatureToSequence, //序列化
		BiLSTM 
	};
#pragma pack(push, 1) 
	struct ModelHeader {
		char magic[8]{ KEY_MAGIC };// "DLRMODL"
		int32_t version{ KEY_VERSION };
		int32_t fileType{ KEY_TYPE_MODEL };//model checkpoint	
	};
#pragma pack(pop)

	struct TensorShape {
		int32_t c{ 0 };
		int32_t w{ 0 };
		int32_t h{ 0 };
	};
	struct NeuralBuild {
		NeuralType type{ NeuralType::Null};
		int32_t c{-1};
		int32_t w{-1};
		int32_t h{-1};
		NeuralBuild& operator=(const NeuralBuild& other) {
			if (this == &other) {
				return *this;
			}
			type = other.type;
			c = other.c;
			w = other.w;
			h = other.h;
			return *this;
		}
		NeuralBuild& operator=(NeuralBuild&& other) noexcept {
			if (this == &other) {
				return *this;
			}
			type = other.type;
			c = other.c;
			w = other.w;
			h = other.h;
			return *this;
		}
		NeuralBuild() = default;
		NeuralBuild(const NeuralBuild& other) = default;
		NeuralBuild(NeuralBuild&& other) noexcept = default;
		NeuralBuild(NeuralType type) {
			this->type = type;
		}

		NeuralBuild(NeuralType type, int32_t c) {
			this->type = type;
			this->c = c;
		}
		NeuralBuild(NeuralType type, int32_t c, int32_t w, int32_t h) {
			this->type = type;
			this->c = c;
			this->w = w;
			this->h = h;
		}
	};
	struct Point2D {
		int32_t x;
		int32_t y;
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