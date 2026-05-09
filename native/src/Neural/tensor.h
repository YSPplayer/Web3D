#pragma once
#include "../define.h"
#include <vector>
#include <string>
namespace DeepLr::Neural {
	class Tensor3D {
	public:
		Tensor3D();
		Tensor3D(int32_t c, int32_t w, int32_t h);
		Tensor3D(const Tensor3D& tensor3D);
		Tensor3D(Tensor3D&& tensor3D);
		Tensor3D& operator=(const Tensor3D& tensor3D);
		Tensor3D& operator=(Tensor3D&& tensor3D) noexcept;
		float Get(int32_t c, int32_t y, int32_t x) const {
			if (y < 0 || y >= h) return 0.0f;
			if(x < 0 || x >= w) return 0.0f;
			return data[(c * h + y) * w + x];
		}
		float Get(int32_t index) const {
			if (index < 0 || index >= data.size()) return 0.0f;
			return data[index];
		}
		float& At(int32_t index) {
			return data[index];
		}
		const float& At(int32_t index) const {
			return data[index];
		}
		float& At(int32_t c, int32_t y, int32_t x) { 
			return data[(c * h + y) * w + x];
		}
		const float& At(int32_t c, int32_t y, int32_t x) const {
			return data[(c * h + y) * w + x];
		}
		void ReShape(int32_t c, int32_t w, int32_t h);
		static Tensor3D Load(const std::string& path);
		inline int32_t Count() const {
			return data.size();
		}
		inline int32_t Height() const {
			return h;
		}
		inline int32_t Width() const {
			return w;
		}
		inline int32_t Channel() const {
			return c;
		}
	private:
		int32_t h;//高度
		int32_t w;//宽度
		int32_t c;//通道
		std::vector<float> data;//数据
	};

}