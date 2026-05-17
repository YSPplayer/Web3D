#pragma once
#include <array>
#include <string>
#include <vector>
#include <memory>
#include "tensor.h"
namespace DeepLr::Neural {
	class Sample {
	public:
		Sample();
		static std::shared_ptr<Sample> Load(const std::string& path, const std::string& imgValue);
		static std::vector<std::shared_ptr<Sample>> Load(const std::string& path);
		inline const Tensor3D* Data() const {
			return &input;
		}
		inline const std::array<int32_t, 4>* Target() const {
			return &target;
		}
	private:
		static std::array<int32_t, 4> ParseLabel(const std::string& imgValue);
		Tensor3D input;//样本值
		std::array<int32_t, 4> target;//标签
		std::string labelText;//标签值
	};
}