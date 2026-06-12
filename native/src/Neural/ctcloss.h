#pragma once
#include <string>
#include <unordered_map>
#include "tensor.h"
namespace DeepLr::Neural {
#define CTC_BLANK '-'
	class CTCLoss {
	public:
		CTCLoss(const std::unordered_map<char, int32_t>& map);
		float Forward(const Tensor3D& input, const std::string& target);
	private:
		std::string ExpandCTC(const std::string& label, char blank = CTC_BLANK);
		std::unordered_map<char,int32_t> map;
	};
}