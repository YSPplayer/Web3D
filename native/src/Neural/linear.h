#pragma once
#include "layer.h"
namespace DeepLr::Neural {
	//行高(row) 列宽(col) 行向量：单行向量 列向量：单列向量
	class Linear : public Layer {
	public:
		Linear(int32_t length);
		Tensor3D Forward(const Tensor3D& input) override;
		Tensor3D Backward(const Tensor3D& output) override;
	private:
		int32_t length;
		Tensor3D w;
		Tensor3D b;
		Tensor3D dw;
		Tensor3D db;
		Tensor3D oldx;//反向传播的时候更新时需要用到
		Tensor3D oldy;//反向传播的时候更新时需要用到
	};
}