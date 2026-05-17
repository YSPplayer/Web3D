#include "linear.h"
#include "../log.h"
#include <format>
namespace DeepLr::Neural {
    Linear::Linear(int32_t lasth, int32_t h):lasth(lasth), h(h){
        ntype = NeuralType::Linear;
        w = Tensor3D(1, lasth, h);
        w.HeUniform(lasth);
        b = Tensor3D(1, 1, h);
        dw  = Tensor3D(1, lasth, h);
        db = Tensor3D(1, 1, h);
    }
    Tensor3D Linear::Forward(const Tensor3D& input, const std::array<int32_t, 4>& target) {
        this->oldx = input;
        this->oldy = w * input + b;
        return this->oldy;
    }
    Tensor3D Linear::Backward(const Tensor3D& output, const std::array<int32_t, 4>& target) {
        Tensor3D temp = output;
        temp.ReShape(1,1, output.Shape());//shape (40,1)
        Tensor3D tempw(this->w); //y = wx + b -> y = w
        tempw.Transpose();
        Tensor3D tempOldx = this->oldx;
        tempOldx.Transpose();
        //´æ´¢WºÍB
        this->dw = dw + temp * tempOldx;
        this->db = db + temp;
        return tempw * temp;
    }
    void Linear::Update(float lr, int32_t batchSize) {
        float oldW0 = w.Count() > 0 ? w.At(0) : 0.0f;
        float oldB0 = b.Count() > 0 ? b.At(0) : 0.0f;
        float dwAbs = dw.SumAbs();
        float dbAbs = db.SumAbs();
        w = w - dw * (lr / (float)batchSize);
        b = b - db * (lr / (float)batchSize);
        if (batchSize <= 8) {
            float newW0 = w.Count() > 0 ? w.At(0) : 0.0f;
            float newB0 = b.Count() > 0 ? b.At(0) : 0.0f;
            Log::Debug(std::format(
                "debug Linear update in={},out={},batch={},dwAbs={},dbAbs={},w0Before={},w0After={},b0Before={},b0After={}",
                lasth, h, batchSize, dwAbs, dbAbs, oldW0, newW0, oldB0, newB0));
        }
        dw = Tensor3D(1, lasth, h);
        db = Tensor3D(1, 1, h);
    }
}