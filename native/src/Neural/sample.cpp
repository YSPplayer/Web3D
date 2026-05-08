#include "sample.h"
#include "../log.h"
namespace DeepLr::Neural {
	Sample::Sample() {
		labelText = "";
		target = std::array<int, 4>();
	}
	Sample Sample::Load(const std::string& path, const std::string& imgValue) {
		Sample sample;
		sample.input = Tensor3D::Load(path);
		sample.target = ParseLabel(imgValue);
		sample.labelText = imgValue;
		return sample;
	}
	std::array<int32_t, 4> Sample::ParseLabel(const std::string& imgValue) {
		if (imgValue.size() != 4) {
			Log::Debug("Expected 4-digit label: " + imgValue);
			return std::array<int32_t, 4>();
		}
		return {
			imgValue[0] - '0',
			imgValue[1] - '0',
			imgValue[2] - '0',
			imgValue[3] - '0'
		};
	}
}