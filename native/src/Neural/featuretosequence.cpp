#include "featuretosequence.h"
namespace DeepLr::Neural {
	FeatureToSequence::FeatureToSequence():Layer(){
		ntype = NeuralType::FeatureToSequence;
	}

	Tensor3D FeatureToSequence::Forward(const Tensor3D& input) { //c,1,w -> w,c[T,F]
		Tensor3D tensor3D(1, input.Channel(), input.Width()); // w,t(w),f(c)
		for (int32_t x = 0; x < input.Width(); ++x) {
			for (int32_t c = 0; c < input.Channel(); ++c) {
				tensor3D.At(0, x, c) = input.Get(c,0,x);
			}
		}
		return tensor3D;
	}

	Tensor3D FeatureToSequence::Backward(const Tensor3D& output, const std::array<int32_t, 4>& target) { //  w,c[T,F] -> c,1,w
		Tensor3D tensor3D(output.Width(), output.Height(),1);
		for (int32_t x = 0; x < output.Height(); ++x) {
			for (int32_t c = 0; c < output.Width(); ++c) {
				tensor3D.At(c, 0, x) = output.Get(0, x, c);
			}
		}
		return tensor3D;
	}

}
